int bind_lsock(int lsock, int port);
void fill_header(char *header, int status, long len, char *type);
void find_mime(char *ct_type, char *uri);
void handle_404(int asock);
void handle_500(int asock);
void http_handler(int asock);
void run_server();