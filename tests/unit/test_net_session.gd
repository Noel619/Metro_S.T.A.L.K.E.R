extends "res://tests/test_case.gd"

const TEST_PORT: int = 24697


func after_each() -> void:
	NetSession.leave()


func test_solo_is_a_host_without_guests() -> void:
	NetSession.start_solo()
	assert_eq(NetSession.mode, NetSession.Mode.SOLO)
	assert_true(NetSession.is_authority(), "en solitario el jugador es el anfitrión")
	assert_eq(NetSession.local_peer_id(), 1)


func test_host_keeps_authority() -> void:
	assert_eq(NetSession.host(TEST_PORT), OK)
	assert_eq(NetSession.mode, NetSession.Mode.HOST)
	assert_true(NetSession.is_authority())
	assert_eq(NetSession.local_peer_id(), 1)


func test_leave_returns_to_solo() -> void:
	assert_eq(NetSession.host(TEST_PORT + 1), OK)
	NetSession.leave()
	assert_eq(NetSession.mode, NetSession.Mode.SOLO)
	assert_true(NetSession.is_authority())


func test_transform_sync_replicates_position_and_rotation() -> void:
	var sync: TransformSync = TransformSync.new()
	var config: SceneReplicationConfig = sync.replication_config
	assert_eq(config.get_properties().size(), 2)
	for path: NodePath in config.get_properties():
		assert_eq(
			config.property_get_replication_mode(path),
			SceneReplicationConfig.REPLICATION_MODE_ALWAYS
		)
	sync.free()
