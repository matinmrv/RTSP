import cv2, imutils, socket
import base64


BUFF_SIZE = 65536
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
host_name = socket.gethostname()
host_ip = "192.168.5.28"  #socket.gethostbyname(host_name)
port = 9999
socket_address = (host_ip, port)
server_socket.bind(socket_address)
print(f"Listening at {socket_address}")

vid_path = "/home/matin/Desktop/TAVideos(1-5)/Session0/session0.mkv"
vid = cv2.VideoCapture(vid_path) 
fps, st, frames_to_count, cnt = 0, 0, 10, 0

while True:
    msg, client_address = server_socket.recvfrom(BUFF_SIZE)
    print(f"Got connection from {client_address}")
    WIDTH = 400
    while(vid.isOpened()):
        _, frame = vid.read()
        frame = imutils.resize(frame, width=WIDTH)
        encoded, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        message = base64.b64encode(buffer)
        server_socket.sendto(message, client_address)
        cv2.imshow("TRANSMITTING VIDEO", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            server_socket.close()
            break
