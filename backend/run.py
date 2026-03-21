from app import app, socketio, start_mqtt

if __name__ == "__main__":
    print("Starting backend + socket server ...")
    start_mqtt()
    socketio.run(app, host="0.0.0.0", port=3000, debug=False)