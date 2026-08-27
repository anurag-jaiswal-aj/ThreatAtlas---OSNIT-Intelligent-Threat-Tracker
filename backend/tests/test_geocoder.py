import pytest
from app.nlp.geocoder import geocode

@pytest.mark.asyncio
async def test_geocode_success_with_country(mocker):
    # Mock httpx.AsyncClient.get
    mock_response = mocker.Mock()
    mock_response.raise_for_status = mocker.Mock()
    mock_response.json.return_value = [
        {
            "lat": "48.8566",
            "lon": "2.3522",
            "address": {
                "country_code": "FR"
            }
        }
    ]

    mock_client_instance = mocker.Mock()
    mock_client_instance.get = mocker.AsyncMock(return_value=mock_response)

    # httpx.AsyncClient is an async context manager
    mock_client_instance.__aenter__ = mocker.AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = mocker.AsyncMock(return_value=None)

    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)

    # Mock DB cache miss
    mock_db = mocker.patch("app.nlp.geocoder.get_database")
    mock_cache = mocker.Mock()
    mock_cache.find_one = mocker.AsyncMock(return_value=None)
    mock_cache.insert_one = mocker.AsyncMock()
    mock_db.return_value.geocache = mock_cache

    res = await geocode("Paris")
    assert res is not None
    lat, lng, cc = res
    assert lat == 48.8566
    assert lng == 2.3522
    assert cc == "fr"  # lowercased

@pytest.mark.asyncio
async def test_geocode_success_without_country(mocker):
    # Mock httpx.AsyncClient.get
    mock_response = mocker.Mock()
    mock_response.raise_for_status = mocker.Mock()
    mock_response.json.return_value = [
        {
            "lat": "48.8566",
            "lon": "2.3522"
        }
    ]

    mock_client_instance = mocker.Mock()
    mock_client_instance.get = mocker.AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = mocker.AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = mocker.AsyncMock(return_value=None)

    mocker.patch("httpx.AsyncClient", return_value=mock_client_instance)

    # Mock DB cache miss
    mock_db = mocker.patch("app.nlp.geocoder.get_database")
    mock_cache = mocker.Mock()
    mock_cache.find_one = mocker.AsyncMock(return_value=None)
    mock_cache.insert_one = mocker.AsyncMock()
    mock_db.return_value.geocache = mock_cache

    res = await geocode("Somewhere")
    assert res is not None
    lat, lng, cc = res
    assert lat == 48.8566
    assert lng == 2.3522
    assert cc is None
