cd server
python setup_server_sdist.py sdist bdist_wheel
python setup_server.py build_exe
cd ..
