from distutils.core import setup

setup(
    name='simple_docker_tool',
    version='1.0.0',
    packages=['simple_docker_tool'],
    py_modules=['simple_docker_tool.simple_docker_api.container_manager', 'simple_docker_tool.simple_docker_api_runner',
                'simple_docker_tool.tests.test_container_manager', ],
    package_data={'simple_docker_tool': ['logging.conf', 'requirements.txt'],
                  },
    data_files=[
        ("Lib/site-packages/simple_docker_tool/docker_image_files", ["simple_docker_tool/docker_image_files/Dockerfile",
                                                                     "simple_docker_tool/docker_image_files/requirements.txt",
                                                                     "simple_docker_tool/docker_image_files/web_app.py"])],

    author='Nikitas Papangelopoulos',
    author_email='npapange@sdsc.edu',
    description='A simple tool to manage containers in Docker.',
    requires=['pypiwin32', 'numpy', 'docker', 'mock', 'nose']
)
