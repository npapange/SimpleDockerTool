#!/usr/bin/python

import logging.config
import unittest

import mock
from mock import MagicMock, patch
from docker.errors import *

from simple_docker_tool.simple_docker_api.container_manager import ContainerManager, DockerImage, DockerContainer

__author__ = 'Nikitas Papangelopoulos'

#logging.config.fileConfig('../logging.conf', disable_existing_loggers=False)


class TestContainerManager(unittest.TestCase):

    @mock.patch('docker.from_env')
    def setUp(self, mock_client):
        self.cm = ContainerManager()
        mock_client.images.build.return_value = MagicMock(short_id='mock_img_short_id', id='mock_img_id',
                                                          tags=['mock_flask'], created_successfully=True)
        mock_client.containers.create.return_value = MagicMock(short_id='mock_cont_short_id', id='mock_cont_id',
                                                               status='created', created_successfully=True)
        mock_client.containers.create().name = 'mock_container'

        self.mock_client = mock_client
        self.cm.docker_client = self.mock_client

    def test_DockerImage_success(self):
        image = DockerImage(self.mock_client, '../docker_image_files', 'flask')
        self.assertEqual(image.short_id, 'mock_img_short_id')
        self.assertEqual(image.id, 'mock_img_id')
        self.assertEqual(image.tag, 'mock_flask')
        self.assertEqual(image.docker_image_obj, self.mock_client.images.build())
        self.assertTrue(image.created_successfully)

    @mock.patch('docker.from_env')
    def test_DockerImage_fail(self, mock_client_error):
        mock_client_error.images.build.side_effect = TypeError
        DockerImage(mock_client_error, 'docker_image_files', 'flask')
        self.assertRaises(TypeError)

    def test_DockerContainer_success(self):
        container_with_name = DockerContainer(self.mock_client, 'mock_img_short_id', 'mock_container', port=5000)
        self.assertEqual(container_with_name.short_id, 'mock_cont_short_id')
        self.assertEqual(container_with_name.id, 'mock_cont_id')
        self.assertEqual(container_with_name.name, 'mock_container')
        self.assertEqual(container_with_name.status, 'created')
        self.assertEqual(container_with_name.container_obj, self.mock_client.containers.create())
        self.assertTrue(container_with_name.created_successfully)
        container_with_name.refresh_status('running')
        self.assertEqual(container_with_name.status, 'running')

        container_no_name = DockerContainer(self.mock_client, 'mock_img_short_id', port=5000)
        self.assertTrue(container_no_name.created_successfully)

    @mock.patch('docker.from_env')
    def test_DockerContainer_fail(self, mock_client_error):
        mock_client_error.containers.create.side_effect = TypeError
        DockerContainer(mock_client_error, 'no_image', port=5000)
        self.assertRaises(TypeError)

    @mock.patch('docker.from_env')
    @mock.patch.dict('os.environ', {'DOCKER_HOST': '', 'DOCKER_TLS_VERIFY': '', 'DOCKER_CERT_PATH': ''})
    def test_ContainerManager_success(self, mock_client):
        cm = ContainerManager()
        self.assertIsNotNone(cm.docker_client)

    @mock.patch.dict('os.environ', {'USERPROFILE': 'C:\\Users\\user_name'})
    def test_ContainerManager_fail(self):
        cm = ContainerManager()
        self.assertFalse('docker_client' in cm.__dict__)

    @mock.patch('docker.from_env')
    @mock.patch.dict('os.environ', {'USERPROFILE': 'C:\\Users\\user_name'})
    def test_ContainerManager_fail_success(self, mock_client):
        cm = ContainerManager()
        self.assertIsNotNone(cm.docker_client)

    def test_build_image_success(self):
        image = self.cm.build_image('../docker_image_files', 'flask')
        self.assertEqual(image.short_id, 'mock_img_short_id')
        self.assertEqual(image.id, 'mock_img_id')
        self.assertEqual(image.tag, 'mock_flask')
        self.assertEqual(image.docker_image_obj, self.mock_client.images.build())
        self.assertTrue(image.created_successfully)

    def test_get_image_success(self):
        with patch.dict(self.cm._ContainerManager__image_dict, {'mock_img_id': DockerImage(self.mock_client, '../docker_image_files', 'flask')}):
            image = self.cm.get_image('mock_img_id')
            self.assertEqual(image.short_id, 'mock_img_short_id')
            self.assertEqual(image.id, 'mock_img_id')
            self.assertEqual(image.tag, 'mock_flask')
            self.assertEqual(image.docker_image_obj, self.mock_client.images.build())
            self.assertTrue(image.created_successfully)

    def test_get_image_fail(self):
        self.cm.get_image('mock_img_id')

    def test_remove_image_success(self):
        with patch.dict(self.cm._ContainerManager__image_dict, {'mock_img_id': DockerImage(self.mock_client, '../docker_image_files', 'flask')}):
            result = self.cm.remove_image('mock_img_id')
            self.assertTrue(result)

    def test_remove_image_fail(self):
        result = self.cm.remove_image('mock_img_id')
        self.assertFalse(result)

    def test_available_images(self):
        with patch.dict(self.cm._ContainerManager__image_dict, {'mock_img_id': DockerImage(self.mock_client, '../docker_image_files', 'flask')}):
            result = self.cm.available_images()
            self.assertIsNotNone(result)

    def test_create_container_success(self):
        container = self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        self.assertEqual(container.short_id, 'mock_cont_short_id')
        self.assertEqual(container.id, 'mock_cont_id')
        self.assertEqual(container.name, 'mock_container')
        self.assertEqual(container.status, 'created')
        self.assertEqual(container.container_obj, self.mock_client.containers.create())

        container_no_port = self.cm.create_container('mock_img_short_id', 'mock_container')
        self.assertEqual(container_no_port.status, 'created')

    @mock.patch('docker.from_env')
    def test_create_container_fail(self, mock_client_error):
        mock_client_error.containers.create.side_effect = TypeError
        self.cm.docker_client = mock_client_error
        container = self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        self.assertIsNone(container)

    def test_start_container_success(self):
        container = self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        self.mock_client.containers.get.start.return_value = True
        self.mock_client.containers.get().status = 'running'
        result = self.cm.start_container('mock_cont_id')
        self.assertTrue(result)
        self.assertEqual(container.status, 'running')

    def test_start_container_fail(self):
        with patch.dict(self.cm._ContainerManager__container_dict, {'mock_cont_id': DockerContainer(self.mock_client, 'mock_img_short_id', 'mock_container')}):
            self.cm.docker_client.containers.get().start.side_effect = APIError('')
            result = self.cm.start_container('mock_cont_id')
            self.assertFalse(result)

    def test_stop_container_success(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        self.cm.start_container('mock_cont_id')
        result = self.cm.stop_container('mock_cont_id')
        self.assertTrue(result)

    def test_stop_container_fail(self):
        self.cm.create_container('mock_img_short_id', 'mock_container')
        self.cm.start_container('mock_cont_id')
        self.cm.docker_client.containers.get().kill.side_effect = APIError('')
        result = self.cm.stop_container('mock_cont_id')
        self.assertFalse(result)

    def test_get_container_success(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        container = self.cm.get_container('mock_cont_id')
        self.assertIsNotNone(container)

    def test_get_container_fail(self):
        container = self.cm.get_container('mock_cont_id')
        self.assertIsNone(container)

    def test_remove_container_success(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        result = self.cm.remove_container('mock_cont_id')
        self.assertTrue(result)

    def test_remove_container_fail(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        self.cm.docker_client.containers.remove.side_effect = APIError('')
        result = self.cm.remove_container('mock_cont_id')
        self.assertFalse(result)

    def test_container_status_success(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        status = self.cm.container_status('mock_cont_id')
        self.assertEqual(status, 'created')

    def test_available_containers_success(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        containers = self.cm.available_containers()
        self.assertEqual(len(containers), 1)

    def test_running_containers_success(self):
        self.cm.create_container('mock_img_short_id', 'mock_container', port=5000)
        self.mock_client.containers.get().status = 'running'
        self.cm.start_container('mock_cont_id')
        containers = self.cm.running_containers()
        self.assertEqual(len(containers), 1)

    def test_running_containers_on_server_success(self):
        container = DockerContainer(self.mock_client, 'mock_img_short_id', 'mock_container', port=5000)
        container.refresh_status('running')
        # This list will contain container objects from the api, not DockerContainer.
        self.cm.docker_client.containers.list.return_value = [container]
        containers = self.cm.running_containers_on_server()
        self.assertEqual(len(containers), 1)
