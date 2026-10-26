# Deployment

The app is a Python server with local models. GitHub Pages cannot run it. A public URL has not been provisioned yet.

## On a server

Use a machine with Python 3.11 or 3.12, Git, and Ollama. Allow several GB of disk space for Python packages and models. The measured setup has 16 GB RAM and an RTX 3060. Test memory use and latency on your target server; CPU inference is supported but will be slower.

Clone this repository and run:

```sh
python setup_project.py
```

Start the service on the server's network interface:

```sh
HOST=0.0.0.0 PORT=8000 python run.py
```

In PowerShell, set `$env:HOST='0.0.0.0'` and `$env:PORT='8000'` first, then run `python run.py`.

Put your host's HTTPS proxy in front of port 8000. Keep Ollama's port 11434 private. Run the app and Ollama under the host's process supervisor so they restart if the machine reboots. For a class demo, restrict access to the class or add rate limiting at the proxy. There is no login system in this small project.

If Ollama runs on another private machine, set `OLLAMA_URL` to its address before setup and execution. The setup script uses the local `ollama pull` command, so pull the generation model on the actual Ollama host in that arrangement.

## Check the deployment

1. Open `/health` and check that the index is loaded. This endpoint does not check the model.
2. Open `/` and ask a Python question to test the full pipeline.
3. Follow the source link and check its quote.
4. Ask an unrelated question and check the refusal.
5. Restart the service and repeat the test.

Add the real HTTPS URL to README.md only after these checks pass. The local URL `http://127.0.0.1:8000` is not a public deployment.
