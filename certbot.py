"""
Errbot commands for interacting with a local certbot installation
"""
# pylint:disable=no-self-use,unused-argument
from itertools import chain
import os
from subprocess import Popen, PIPE

from errbot import BotPlugin, botcmd


CERBOT_TEMPLATE = {
    'cert_paths': [],
    'certbot': '/path/to/certbot-auto',
    'channel': '#general',
}


class CommandError(Exception):
    """An error raised by a command, nbd."""
    pass


class Certbot(BotPlugin):
    """
    Errbot plugin for running commands for sys-administration of dancohen.io.
    """
    def get_configuration_template(self):
        """
        Return the default or active configuration.
        """
        return CERBOT_TEMPLATE

    def configure(self, configuration):
        """Set the configuration for the kodi plugin."""
        if configuration is not None and configuration != {}:
            config = dict(chain(CERBOT_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = CERBOT_TEMPLATE
        super(Certbot, self).configure(config)

    def activate(self):
        """
        Set scheduled commands.
        """
        super(Certbot, self).activate()
        self.start_poller(60 * 60 * 24 * 14, self._print_renew_certs)

    def _send_output_to_channel(self, func):
        """
        Run the given method and send its output to the configured channel.
        """
        channel = self.build_identifier(self.config.channel)
        for line in func():
            self.send(channel, line)

    def _print_renew_certs(self):
        """
        Run _call_renew_certs and print the output to the configured channel.
        """
        self._send_output_to_channel(self._call_renew_certs)

    def popen(self, args):
        """
        Run a command locally.
        """
        sp = Popen(args, stdout=PIPE, stderr=PIPE)
        for line in iter(sp.stdout.readline, b''):
            try:
                line = line.decode('utf_8').strip()
            except UnicodeDecodeError as e:
                line = '-----%s-----' % e
            yield line
        sp.wait()
        if sp.returncode > 0:
            raise CommandError(sp)

    def _call_renew_certs(self):
        """
        Make the call to renew certificates.
        """
        cmd_args = [
            'sudo',
            self.config['certbot'],
            'renew',
            '--non-interactive',
        ]
        for line in self.popen(cmd_args):
            yield line

    @botcmd
    def certbot_certificates(self, message, args):
        """
        Return the cert expiration date.
        """
        cmd_args = ['sudo', self.config['certbot'], 'certificates']
        for line in self.popen(cmd_args):
            yield line

    @botcmd
    def certbot_help(self, message, args):
        """
        Ask the cerbot executable for --help.
        """
        for line in self.popen([self.config['certbot'], '--help']):
            yield line

    @botcmd
    def cerbot_renew(self, message, args):
        """
        Use cerbot to automatically renew known certs.
        """
        for line in self._call_renew_certs():
            yield line

    @botcmd
    def add_cert(self, message, args):
        """
        Add a given cert path to the stored configuration.
        """
        if not args:
            yield "certificate can not be empty."
        elif args in self.config['cert_paths']:
            yield "'%s' is already in cert_paths" % args
        elif not os.path.exists(args):
            yield "Cound not find path: '%s'" % args
        else:
            self.config['cert_paths'].append(args)
            yield "Added new cert path: '%s'" % args
            yield "cert_paths: %s" % self.config['cert_paths']
