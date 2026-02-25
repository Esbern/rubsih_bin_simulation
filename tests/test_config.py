from simulated_city.config import load_config


def test_load_config_defaults_when_missing(tmp_path) -> None:
    cfg = load_config(tmp_path / "missing.yaml")
    assert cfg.mqtt.host
    assert cfg.mqtt.port


def test_load_config_reads_yaml(tmp_path) -> None:
    p = tmp_path / "config.yaml"
    p.write_text(
        """
        mqtt:
          host: example.com
          port: 1883
          tls: false
          client_id_prefix: demo
          keepalive_s: 30
          base_topic: test
        """.strip(),
        encoding="utf-8",
    )

    cfg = load_config(p)
    assert cfg.mqtt.host == "example.com"
    assert cfg.mqtt.port == 1883
    assert cfg.mqtt.tls is False
    assert cfg.mqtt.client_id_prefix == "demo"
    assert cfg.mqtt.keepalive_s == 30
    assert cfg.mqtt.base_topic == "test"


def test_load_config_finds_parent_config_yaml(tmp_path, monkeypatch) -> None:
        # Simulate running from a subdirectory (like notebooks/)
        root = tmp_path
        (root / "config.yaml").write_text(
                """
                mqtt:
                    host: parent.example.com
                    port: 1883
                    tls: false
                    client_id_prefix: demo
                    keepalive_s: 30
                    base_topic: test
                """.strip(),
                encoding="utf-8",
        )

        subdir = root / "notebooks"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        cfg = load_config("config.yaml")
        assert cfg.mqtt.host == "parent.example.com"


def test_load_config_supports_mqtt_profiles(tmp_path) -> None:
        p = tmp_path / "config.yaml"
        p.write_text(
                """
                mqtt:
                    profile: local
                    profiles:
                        local:
                            host: 127.0.0.1
                            port: 1883
                            tls: false
                        mqtthq:
                            host: broker.mqttdashboard.com
                            port: 1883
                            tls: false
                    client_id_prefix: demo
                    keepalive_s: 30
                    base_topic: test
                """.strip(),
                encoding="utf-8",
        )

        cfg = load_config(p)
        assert cfg.mqtt.host == "127.0.0.1"
        assert cfg.mqtt.port == 1883
        assert cfg.mqtt.tls is False
        assert cfg.mqtt.client_id_prefix == "demo"
        assert cfg.mqtt.keepalive_s == 30
        assert cfg.mqtt.base_topic == "test"


def test_load_config_mqtt_profile_can_be_selected_by_env_var(tmp_path, monkeypatch) -> None:
        p = tmp_path / "config.yaml"
        p.write_text(
                """
                mqtt:
                    profile: local
                    profiles:
                        local:
                            host: 127.0.0.1
                            port: 1883
                            tls: false
                        mqtthq:
                            host: broker.mqttdashboard.com
                            port: 1883
                            tls: false
                """.strip(),
                encoding="utf-8",
        )

        monkeypatch.setenv("SIMCITY_MQTT_PROFILE", "mqtthq")
        cfg = load_config(p)
        assert cfg.mqtt.host == "broker.mqttdashboard.com"
