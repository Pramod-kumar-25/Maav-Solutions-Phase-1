import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.filing_service import FilingService
from app.core.exceptions import ValidationError, DuplicateResourceError, NotFoundError
from app.schemas.filing import FilingCreate

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_filing_repo():
    """Mock for the Filing Case Repository with explicitly declared methods."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    # Default successful creation returns a DRAFT state
    repo.create.return_value = MagicMock(id=uuid4(), status="DRAFT")
    return repo


@pytest.fixture
def service(mock_filing_repo):
    """Instantiate the Service with mocked dependencies."""
    return FilingService(filing_repo=mock_filing_repo)


@pytest.fixture
def filing_id():
    return uuid4()


@pytest.fixture
def mock_session():
    return AsyncMock()


async def test_create_filing_success(service, mock_filing_repo, mock_session):
    """
    Test Case: test_create_filing_success
    - Valid taxpayer
    - Filing starts in DRAFT state
    - Ensure repo.create is called once
    """
    # Arrange
    taxpayer_id = uuid4()
    filing_data = FilingCreate(taxpayer_id=taxpayer_id, financial_year="2023-24")

    # Act
    result = await service.create_filing(mock_session, filing_data)

    # Assert
    assert result is not None
    assert result.id is not None
    assert result.status == "DRAFT"

    # Ensure creation happened exactly once
    mock_filing_repo.create.assert_called_once()
    create_args = mock_filing_repo.create.call_args[0]
    assert create_args[0] == mock_session


async def test_valid_state_transition_draft_to_ready(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_valid_state_transition_draft_to_ready
    - Transition from DRAFT → READY
    - Ensure repo.update is called once
    - Ensure state updated correctly
    """
    # Arrange: Simulate an existing DRAFT filing
    mock_filing = MagicMock(id=filing_id, status="DRAFT")
    mock_filing_repo.get_by_id.return_value = mock_filing

    # Act
    await service.transition_state(mock_session, filing_id, "READY")

    # Assert
    assert mock_filing_repo.update.call_count == 1
    _, _, payload = mock_filing_repo.update.call_args[0]
    assert payload.get("status") == "READY"


async def test_invalid_state_transition(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_invalid_state_transition
    - Attempt invalid transition (DRAFT → VERIFIED)
    - Ensure ValidationError is raised
    - Ensure repo.update.call_count == 0
    """
    # Arrange: Start in DRAFT
    mock_filing = MagicMock(id=filing_id, status="DRAFT")
    mock_filing_repo.get_by_id.return_value = mock_filing

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.transition_state(mock_session, filing_id, "VERIFIED")

    # Enforce strictly zero write operations on failure
    assert mock_filing_repo.update.call_count == 0


async def test_submit_without_ready_state(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_submit_without_ready_state
    - Attempt DRAFT → SUBMITTED directly
    - Ensure error is raised
    - Ensure no update call happens
    """
    # Arrange: Start in DRAFT
    mock_filing = MagicMock(id=filing_id, status="DRAFT")
    mock_filing_repo.get_by_id.return_value = mock_filing

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.transition_state(mock_session, filing_id, "SUBMITTED")

    # Strictly zero write operations on failure
    assert mock_filing_repo.update.call_count == 0


async def test_verify_without_submission(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_verify_without_submission
    - Attempt READY → VERIFIED
    - Ensure error is raised
    - Ensure repo.update.call_count == 0
    """
    # Arrange: Start in READY
    mock_filing = MagicMock(id=filing_id, status="READY")
    mock_filing_repo.get_by_id.return_value = mock_filing

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.transition_state(mock_session, filing_id, "VERIFIED")

    # Strictly zero write operations on failure
    assert mock_filing_repo.update.call_count == 0


async def test_duplicate_submission(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_duplicate_submission
    - Attempt SUBMITTED → SUBMITTED again
    - Ensure DuplicateResourceError or ValidationError
    - Ensure repo.update.call_count == 0
    """
    # Arrange: Start already in SUBMITTED
    mock_filing = MagicMock(id=filing_id, status="SUBMITTED")
    mock_filing_repo.get_by_id.return_value = mock_filing

    # Act & Assert
    with pytest.raises((DuplicateResourceError, ValidationError)):
        await service.transition_state(mock_session, filing_id, "SUBMITTED")

    # Strictly zero write operations on failure
    assert mock_filing_repo.update.call_count == 0


async def test_transition_filing_not_found(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_transition_filing_not_found
    - Simulate repo.get_by_id returning None
    - Ensure service raises NotFoundError
    - Ensure repo.update.call_count == 0
    """
    # Arrange
    mock_filing_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.transition_state(mock_session, filing_id, "READY")

    # Ensure update is never triggered
    assert mock_filing_repo.update.call_count == 0


async def test_successful_full_flow(service, mock_filing_repo, mock_session, filing_id):
    """
    Test Case: test_successful_full_flow
    - DRAFT → READY → SUBMITTED → VERIFIED
    - Ensure each step updates correctly
    """
    # --- Step 1: DRAFT -> READY ---
    mock_filing = MagicMock(id=filing_id, status="DRAFT")
    mock_filing_repo.get_by_id.return_value = mock_filing

    await service.transition_state(mock_session, filing_id, "READY")
    assert mock_filing_repo.update.call_count == 1
    _, _, payload = mock_filing_repo.update.call_args[0]
    assert payload.get("status") == "READY"

    # --- Step 2: READY -> SUBMITTED ---
    mock_filing.status = "READY"
    mock_filing_repo.update.reset_mock()

    await service.transition_state(mock_session, filing_id, "SUBMITTED")
    assert mock_filing_repo.update.call_count == 1
    _, _, payload = mock_filing_repo.update.call_args[0]
    assert payload.get("status") == "SUBMITTED"

    # --- Step 3: SUBMITTED -> VERIFIED ---
    mock_filing.status = "SUBMITTED"
    mock_filing_repo.update.reset_mock()

    await service.transition_state(mock_session, filing_id, "VERIFIED")
    assert mock_filing_repo.update.call_count == 1
    _, _, payload = mock_filing_repo.update.call_args[0]
    assert payload.get("status") == "VERIFIED"
