from simulated_city.config import MqttConfig
from simulated_city.mqtt import topic


def test_mqtt_topic_builder() -> None:
    cfg = MqttConfig(
        host="example.com",
        port=1883,
        tls=False,
        username=None,
        password=None,
        client_id_prefix="demo",
        keepalive_s=60,
        base_topic="simulated-city",
    )

    assert topic(cfg, "") == "simulated-city"
    assert topic(cfg, "/events") == "simulated-city/events"
    assert topic(cfg, "events") == "simulated-city/events"
