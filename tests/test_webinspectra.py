from webinspectra import WebInspectra

def test_google_inspect():
    google_url = "https://www.google.com"
    result = WebInspectra().inspect(google_url)

    assert isinstance(result, dict)
    assert "technologies" in result
    assert "count" in result
    assert result["count"] > 0
    assert "Google Web Server" in result['technologies']
    assert "description" in result['technologies']['Google Web Server']
    assert result['technologies']['Google Web Server']['description'] != ""

def test_vulnweb_inspect():
    url = "http://testphp.vulnweb.com"
    result = WebInspectra().inspect(url)

    assert isinstance(result, dict)
    assert "technologies" in result
    assert "count" in result
    assert result["count"] > 0
    assert "Ubuntu" in result['technologies']
    assert "description" in result['technologies']['Ubuntu']
    assert result['technologies']['Ubuntu']['description'] != ""
    assert "PHP" in result['technologies']
    assert "Nginx" in result['technologies']
