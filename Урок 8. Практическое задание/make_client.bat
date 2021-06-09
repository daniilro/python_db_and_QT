cd client
python setup_client_sdist.py sdist bdist_wheel
python setup_client.py build_exe
cd ..
