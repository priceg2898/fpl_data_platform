from unittest.mock import MagicMock, patch
from shared.connectors.mssql import mssql_connection


@patch("shared.connectors.mssql.pyodbc.connect")
def test_mssql_connection(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    with mssql_connection(
        server="localhost",
        database="testdb",
        username="sa",
        password="secret",
    ) as conn:
        assert conn is mock_conn

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()
    mock_conn.close.assert_called_once()
