import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal

from app.services.financial_service import FinancialEntryService
from app.core.exceptions import ValidationError, NotFoundError

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_financial_repo():
    """Mock for the Financial Entry Repository with explicitly declared methods."""
    repo = AsyncMock()
    repo.create_entry = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_entries_by_user = AsyncMock()
    # Default successful creation returns a valid entry
    repo.create_entry.return_value = MagicMock(
        id=uuid4(),
        user_id=uuid4(),
        type="INCOME",
        amount=Decimal("50000.00"),
        description="Salary",
        financial_year="2023-24"
    )
    return repo


@pytest.fixture
def service(mock_financial_repo):
    """Instantiate the Service with mocked dependencies."""
    return FinancialEntryService(financial_repo=mock_financial_repo)


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def mock_session():
    return AsyncMock()


async def test_create_entry_success(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_create_entry_success
    - Valid INCOME entry with positive amount
    - Ensure entry is created
    - Ensure repo.create_entry is called once
    """
    # Arrange
    entry_data = {
        "type": "INCOME",
        "amount": Decimal("50000.00"),
        "description": "Salary",
        "financial_year": "2023-24"
    }

    # Act
    result = await service.create_entry(mock_session, user_id, entry_data)

    # Assert
    assert result is not None
    assert result.id is not None
    mock_financial_repo.create_entry.assert_called_once()


async def test_create_expense_entry_success(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_create_expense_entry_success
    - Valid EXPENSE entry with positive amount
    - Ensure entry is created
    - Ensure repo.create_entry is called once
    """
    # Arrange
    mock_financial_repo.create_entry.return_value = MagicMock(
        id=uuid4(),
        user_id=user_id,
        type="EXPENSE",
        amount=Decimal("15000.00"),
        description="Office Rent",
        financial_year="2023-24"
    )
    entry_data = {
        "type": "EXPENSE",
        "amount": Decimal("15000.00"),
        "description": "Office Rent",
        "financial_year": "2023-24"
    }

    # Act
    result = await service.create_entry(mock_session, user_id, entry_data)

    # Assert
    assert result is not None
    assert result.id is not None
    assert result.type == "EXPENSE"
    mock_financial_repo.create_entry.assert_called_once()


async def test_negative_amount_rejected(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_negative_amount_rejected
    - Provide negative amount
    - Ensure ValidationError is raised
    - Ensure repo.create_entry.call_count == 0
    """
    # Arrange
    entry_data = {
        "type": "INCOME",
        "amount": Decimal("-5000.00"),
        "description": "Invalid Entry",
        "financial_year": "2023-24"
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.create_entry(mock_session, user_id, entry_data)

    # Zero write operations on failure
    assert mock_financial_repo.create_entry.call_count == 0


async def test_invalid_type_rejected(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_invalid_type_rejected
    - Provide invalid entry type (not INCOME or EXPENSE)
    - Ensure ValidationError is raised
    - Ensure repo.create_entry.call_count == 0
    """
    # Arrange
    entry_data = {
        "type": "REFUND",
        "amount": Decimal("1000.00"),
        "description": "Invalid Type",
        "financial_year": "2023-24"
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.create_entry(mock_session, user_id, entry_data)

    # Zero write operations on failure
    assert mock_financial_repo.create_entry.call_count == 0


async def test_fetch_entries_by_user(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_fetch_entries_by_user
    - Fetch all entries for a user
    - Ensure repo.get_entries_by_user is called once
    - Ensure result is a list
    """
    # Arrange
    mock_financial_repo.get_entries_by_user.return_value = [
        MagicMock(id=uuid4(), type="INCOME", amount=Decimal("50000.00")),
        MagicMock(id=uuid4(), type="EXPENSE", amount=Decimal("10000.00")),
    ]

    # Act
    result = await service.get_entries(mock_session, user_id)

    # Assert
    assert result is not None
    assert len(result) == 2
    mock_financial_repo.get_entries_by_user.assert_called_once_with(mock_session, user_id)


async def test_get_entry_not_found(service, mock_financial_repo, mock_session):
    """
    Test Case: test_get_entry_not_found
    - Simulate repo.get_by_id returning None
    - Ensure NotFoundError is raised
    """
    # Arrange
    entry_id = uuid4()
    mock_financial_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.get_entry_by_id(mock_session, entry_id)


async def test_zero_amount_accepted(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_zero_amount_accepted
    - Amount of exactly 0 should be valid (>= 0 constraint)
    - Ensure repo.create_entry is called once
    """
    # Arrange
    mock_financial_repo.create_entry.return_value = MagicMock(
        id=uuid4(),
        type="EXPENSE",
        amount=Decimal("0.00")
    )
    entry_data = {
        "type": "EXPENSE",
        "amount": Decimal("0.00"),
        "description": "Zero adjustment",
        "financial_year": "2023-24"
    }

    # Act
    result = await service.create_entry(mock_session, user_id, entry_data)

    # Assert
    assert result is not None
    mock_financial_repo.create_entry.assert_called_once()


# ============================================================
# EXPENSE-Specific Validation Suite
# ============================================================

async def test_create_expense_success(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_create_expense_success
    - Valid EXPENSE entry with positive amount
    - Ensure entry is created with type EXPENSE
    - Ensure repo.create_entry is called once
    """
    # Arrange
    mock_financial_repo.create_entry.return_value = MagicMock(
        id=uuid4(),
        user_id=user_id,
        type="EXPENSE",
        amount=Decimal("25000.00"),
        description="Professional Services",
        financial_year="2023-24"
    )
    entry_data = {
        "type": "EXPENSE",
        "amount": Decimal("25000.00"),
        "description": "Professional Services",
        "financial_year": "2023-24"
    }

    # Act
    result = await service.create_entry(mock_session, user_id, entry_data)

    # Assert
    assert result is not None
    assert result.id is not None
    assert result.type == "EXPENSE"
    assert result.amount == Decimal("25000.00")
    mock_financial_repo.create_entry.assert_called_once()


async def test_expense_negative_amount(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_expense_negative_amount
    - EXPENSE with negative amount
    - Ensure ValidationError is raised
    - Ensure repo.create_entry.call_count == 0
    """
    # Arrange
    entry_data = {
        "type": "EXPENSE",
        "amount": Decimal("-8000.00"),
        "description": "Invalid Expense",
        "financial_year": "2023-24"
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.create_entry(mock_session, user_id, entry_data)

    # Zero write operations on failure
    assert mock_financial_repo.create_entry.call_count == 0


async def test_expense_invalid_type(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_expense_invalid_type
    - Entry with type "DEDUCTION" instead of EXPENSE
    - Ensure ValidationError is raised
    - Ensure repo.create_entry.call_count == 0
    """
    # Arrange
    entry_data = {
        "type": "DEDUCTION",
        "amount": Decimal("3000.00"),
        "description": "Invalid Type Expense",
        "financial_year": "2023-24"
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.create_entry(mock_session, user_id, entry_data)

    # Zero write operations on failure
    assert mock_financial_repo.create_entry.call_count == 0


async def test_fetch_expense_entries(service, mock_financial_repo, mock_session, user_id):
    """
    Test Case: test_fetch_expense_entries
    - Fetch entries filtered to EXPENSE type
    - Ensure repo.get_entries_by_user is called once
    - Ensure all returned entries are EXPENSE type
    """
    # Arrange
    mock_financial_repo.get_entries_by_user.return_value = [
        MagicMock(id=uuid4(), type="EXPENSE", amount=Decimal("12000.00"), description="Office Rent"),
        MagicMock(id=uuid4(), type="EXPENSE", amount=Decimal("5000.00"), description="Utilities"),
        MagicMock(id=uuid4(), type="EXPENSE", amount=Decimal("3500.00"), description="Travel"),
    ]

    # Act
    result = await service.get_entries(mock_session, user_id, entry_type="EXPENSE")

    # Assert
    assert result is not None
    assert len(result) == 3
    for entry in result:
        assert entry.type == "EXPENSE"
    mock_financial_repo.get_entries_by_user.assert_called_once()
