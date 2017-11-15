"""
Tests for the certbot plugin
"""
# pylint:disable=protected-access
from __future__ import print_function
import os

import certbot


pytest_plugins = ["errbot.backends.test"]

extra_plugin_dir = '.'

def mock_popen(*args, **kwargs):
    """Just yield some strings."""
    for x in range(1):
        yield str(x)

def get_bot(testbot):
    """
    Return a bot with mocked popen method.
    """
    bot = testbot._bot.plugin_manager.get_plugin_obj_by_name(
        'Certbot'
    )
    bot.popen = mock_popen
    return bot

def test_popen(testbot):
    """
    Test the popen method.
    """
    bot = get_bot(testbot)
    for _ in bot.popen(['echo', 'foobar']):
        pass

def test_popen_mock(testbot):
    """
    Test the popen method (and test that it's been patched succesfully)
    """
    bot = get_bot(testbot)
    for _ in bot.popen(['which', 'foobar']):
        pass

def test_send_output_to_channel(testbot):
    """
    Test the funtion that runs another function in the configured channel.
    """
    bot = get_bot(testbot)
    def print_some_text():
        """Demo function to pass in as arg"""
        for line in ['start', 'finish']:
            yield line

    bot._send_output_to_channel(print_some_text)

    result = testbot.pop_message()
    print(result)
    assert 'start' in result

def test_print_renew_certs(testbot):
    """
    Print the renew certs method without it being triggered by a bot command.
    (Used for scheduling the command.)
    """
    bot = get_bot(testbot)
    bot._print_renew_certs()
    testbot.pop_message()
    result = testbot.pop_message()
    assert 'Done!' in result

def test_certbot_renew(testbot):
    """
    Test certbot renew bot command.
    """
    bot = get_bot(testbot)
    testbot.push_message('!certbot renew')
    testbot.pop_message()
    result = testbot.pop_message()
    assert 'Done!' in result

def test_cerbot_certificates(testbot):
    """
    Runs the cerbot command to list certifictes.
    """
    bot = get_bot(testbot)
    testbot.push_message('!certbot certificates')
    testbot.pop_message()
    result = testbot.pop_message()
    assert 'Done!' in result

def test_certbot_help(testbot):
    """
    Get the help output.
    """
    bot = get_bot(testbot)
    testbot.push_message('!certbot help')
    result = testbot.pop_message()
    assert 'Asking certbot' in result

def test_add_cert(testbot):
    """
    Add a new cert to the configuration.
    """
    bot = get_bot(testbot)
    filepath = os.path.abspath(__file__)
    testbot.push_message('!add cert %s' % filepath)
    result = testbot.pop_message()
    assert 'Added new cert' in result

def test_add_cert_empty(testbot):
    """
    Add a new cert to the configuration.
    """
    testbot.push_message('!add cert')
    result = testbot.pop_message()
    assert "Certificate can not be empty." in result

def test_add_cert_missing(testbot):
    """
    Add a new cert to the configuration.
    """
    testbot.push_message('!add cert foobar')
    result = testbot.pop_message()
    assert "Cound not find path:" in result

def test_add_cert_dupe(testbot):
    """
    Add a new cert to the configuration.
    """
    filepath = os.path.abspath(__file__)
    testbot.push_message('!add cert %s' % filepath)
    testbot.pop_message()
    testbot.pop_message()
    testbot.push_message('!add cert %s' % filepath)
    result = testbot.pop_message()
    assert 'already in cert_paths' in result
