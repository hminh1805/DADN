from app import app, socketio

if __name__ == "__main__":
    print("Starting backend + socket server ...")
    socketio.run(app, host="0.0.0.0", port=3000, debug=False)