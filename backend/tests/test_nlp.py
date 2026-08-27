import pytest
from app.nlp.service import nlp_service
from app.nlp.preprocessing import clean_text

def test_clean_text():
    raw_html = "<p>This is a <b>test</b>.</p> See more at http://example.com/test  \n\n\t"
    cleaned = clean_text(raw_html)
    assert cleaned == "This is a test . See more at"

@pytest.mark.asyncio
async def test_process_text(mocker):
    # Mock geocoder to prevent actual HTTP requests during tests
    mocker.patch("app.nlp.service.geocode", return_value=(48.8566, 2.3522, "fr"))
    
    text = "Reports of an explosion near Paris today. Several T-72 tanks were seen."
    result = await nlp_service.process_text(text)
    
    # We expect 'Paris' to be in locations due to 'GPE' extraction
    assert any(loc.name.lower() == "paris" for loc in result.locations)
    assert any(loc.lat == 48.8566 and loc.lng == 2.3522 and loc.country_code == "fr" for loc in result.locations)
    
    # We expect 'explosion' to be in event_types
    assert "explosion" in result.event_types
    
    # We expect 'T-72' to be in equipment
    assert "T-72" in result.equipment
