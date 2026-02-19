from core.ddragon import parse_champions


def test_parse_champions_extracts_fields() -> None:
    payload = {
        "data": {
            "Aatrox": {
                "key": "266",
                "name": "Aatrox",
                "tags": ["Fighter", "Tank"],
                "image": {"full": "Aatrox.png"},
            }
        }
    }
    champs = parse_champions(payload, "14.10.1")
    assert len(champs) == 1
    assert champs[0].id == 266
    assert champs[0].name == "Aatrox"
    assert champs[0].icon_url.endswith("Aatrox.png")
