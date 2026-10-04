import json
from pathlib import Path
import tempfile
import unittest

from ci.prepare_deployment import write_configuration


class PipelineConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.values = dict(DEPLOY_HOST='192.168.1.50', DEPLOY_USER='ubuntu',
                           DEPLOY_SSH_PORT='22', DEPLOY_APP_PORT='8080',
                           REPAIR_IMAGE='repair-tracker:build-15-abcd1234')

    def tearDown(self):
        self.temp.cleanup()

    def test_structured_inventory_and_image_reference(self):
        write_configuration(self.values, self.workspace)
        inventory = json.loads((self.workspace / 'tmp/jenkins-inventory.json').read_text())
        host = inventory['repair_servers']['hosts']['repair-server']
        self.assertEqual(host['ansible_host'], '192.168.1.50')
        self.assertEqual(host['ansible_port'], 22)
        variables = json.loads((self.workspace / 'tmp/deploy-vars.json').read_text())
        self.assertEqual(variables['repair_image_ref'], self.values['REPAIR_IMAGE'])
        self.assertEqual(Path(variables['repair_image_archive']), self.workspace / 'tmp/repair-image.tar')

    def test_invalid_parameters_are_rejected(self):
        for key, value in [('DEPLOY_HOST', ''), ('DEPLOY_HOST', 'host; echo bad'),
                           ('DEPLOY_USER', 'user name'), ('DEPLOY_SSH_PORT', '0'),
                           ('DEPLOY_APP_PORT', '99999'), ('REPAIR_IMAGE', 'bad image')]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                write_configuration({**self.values, key: value}, self.workspace)


if __name__ == '__main__':
    unittest.main()
