def test_bashrc(host):
    bashrc = host.file("/home/operator/.bashrc")
    assert bashrc.contains("source /opt/ros/melodic/setup.bash")

def test_operator_is_user(host):
    user = host.user('operator')
    assert user.uid

# def test_rostopic(host):
#     cmd = host.run('rostopic list')
#     assert cmd.rc == 0

# def test_rostopic_exists(host):
#     exists = host.exists('rostopic')
#     assert exists