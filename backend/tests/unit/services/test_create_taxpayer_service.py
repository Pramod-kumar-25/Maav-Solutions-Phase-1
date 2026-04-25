import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

# Assuming typical imports based on the project's architecture
from app.schemas.taxpayer import TaxpayerProfileCreate
from app.services.taxpayer_service import TaxpayerProfileService
from app.core.exceptions import ValidationError, DuplicateResourceError, NotFoundError

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_taxpayer_repo():
    """Mock for the Taxpayer Profile Repository."""
    repo = AsyncMock()
    # By default, assume the taxpayer doesn't exist to allow creation
    repo.get_by_user_id.return_value = None
    repo.create.return_value = MagicMock(id=uuid4(), residential_status="RESIDENT")
    return repo

@pytest.fixture
def mock_user_repo():
    """Mock for the User Repository to check PAN types."""
    repo = AsyncMock()
    # By default, setup a user with a valid individual PAN type ('P' is the 4th character)
    mock_user = MagicMock()
    mock_user.pan_number = "ABCPD1234E"
    repo.get_by_id.return_value = mock_user
    return repo

@pytest.fixture
def service(mock_taxpayer_repo, mock_user_repo):
    """Instantiate the Service with mocked dependencies."""
    return TaxpayerProfileService(
        taxpayer_repo=mock_taxpayer_repo,
        user_repo=mock_user_repo
    )

@pytest.fixture
def user_id():
    return uuid4()

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def valid_profile_data():
    return TaxpayerProfileCreate(
        days_in_india_current_fy=182,
        days_in_india_last_4_years=400,
        has_foreign_income=False,
        default_tax_regime="NEW",
        aadhaar_link_status=True
    )


async def test_create_taxpayer_success(service, mock_taxpayer_repo, mock_user_repo, user_id, valid_profile_data, mock_session):
    """
    Test Case: test_create_taxpayer_success
    - Valid input
    - Ensure taxpayer profile is created
    - Ensure repository create method is called once
    """
    # Arrange (Done via fixtures)

    # Act
    result = await service.create_profile(mock_session, user_id, valid_profile_data)

    # Assert
    assert result is not None
    assert result.id is not None
    
    # Verify dependencies were queried correctly before creation
    mock_user_repo.get_by_id.assert_called_once_with(mock_session, user_id)
    mock_taxpayer_repo.get_by_user_id.assert_called_once_with(mock_session, user_id)
    
    # Verify the write operation fired correctly
    mock_taxpayer_repo.create.assert_called_once()
    
    # Ensure correct arguments were passed to the repository payload
    _, payload = mock_taxpayer_repo.create.call_args[0]
    assert payload["user_id"] == user_id
    assert payload["days_in_india_current_fy"] == valid_profile_data.days_in_india_current_fy


async def test_create_taxpayer_duplicate(service, mock_taxpayer_repo, mock_session, user_id, valid_profile_data):
    """
    Test Case: test_create_taxpayer_duplicate
    - Simulate existing taxpayer using mock
    - Ensure service raises DuplicateResourceError
    """
    # Arrange: Simulate an already existing taxpayer profile for this user
    mock_taxpayer_repo.get_by_user_id.return_value = MagicMock()

    # Act & Assert
    with pytest.raises(DuplicateResourceError):
        await service.create_profile(mock_session, user_id, valid_profile_data)
    
    # Ensure creation is NEVER triggered
    assert mock_taxpayer_repo.create.call_count == 0


async def test_create_taxpayer_invalid_pan_type(service, mock_taxpayer_repo, mock_user_repo, mock_session, user_id, valid_profile_data):
    """
    Test Case: test_create_taxpayer_invalid_pan_type
    - Provide invalid PAN type (e.g., 'C' for Company)
    - Ensure service rejects input
    """
    # Arrange: Overwrite the user mock to have an invalid individual PAN (4th character 'C')
    mock_user = MagicMock()
    mock_user.pan_number = "ABCCD1234E"
    mock_user_repo.get_by_id.return_value = mock_user

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.create_profile(mock_session, user_id, valid_profile_data)
        
    assert mock_taxpayer_repo.create.call_count == 0


async def test_create_taxpayer_user_not_found(service, mock_taxpayer_repo, mock_user_repo, mock_session, user_id, valid_profile_data):
    """
    Test Case: test_create_taxpayer_user_not_found
    - Simulate user_repo.get_by_id returning None
    - Ensure service raises NotFoundError
    - Ensure no repository create call happens
    """
    # Arrange
    mock_user_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.create_profile(mock_session, user_id, valid_profile_data)

    # Ensure creation is never triggered
    assert mock_taxpayer_repo.create.call_count == 0


async def test_create_taxpayer_sets_default_values(service, mock_taxpayer_repo, mock_session, user_id):
    """
    Test Case: test_create_taxpayer_sets_default_values
    - Ensure default fields (regime, status, etc.) are correctly set
    """
    # Arrange: Provide minimal data, relying on schemas/service logic to populate defaults
    minimal_profile_data = TaxpayerProfileCreate(
        days_in_india_current_fy=45
    )

    # Act
    await service.create_profile(mock_session, user_id, minimal_profile_data)

    # Assert
    mock_taxpayer_repo.create.assert_called_once()
    _, payload = mock_taxpayer_repo.create.call_args[0]
    
    # Verify the service logically filled in derived or default values
    assert payload.get("default_tax_regime") == "NEW"
    assert "residential_status" in payload
    assert payload.get("has_foreign_income") is False
    assert payload.get("aadhaar_link_status") is False
