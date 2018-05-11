from io import BytesIO, StringIO

from flag_slurper.autolib import post


def test_pos_ssh(mock, sudocred):
    """
    TODO This clearly needs to be a lot better.
    """
    ssh = mock.MagicMock()
    mock.patch('flag_slurper.autolib.post.get_directory')

    run_sudo = mock.patch('flag_slurper.autolib.post.run_sudo')
    run_sudo.return_value = [StringIO(), BytesIO(b""), BytesIO()]

    ssh.exec_command.return_value = [StringIO(), BytesIO(b""), BytesIO()]

    post.post_ssh(ssh, sudocred)

    assert run_sudo.called
    assert ssh.exec_command.called
