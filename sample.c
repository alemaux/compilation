
typedef struct{
    int x;
    int y;
    }Point;    

typedef struct{
    Point A;
    Point B;
}Ligne;

int main(int X, int Y) {
    Point P;
    Point Q;
    Q.x = 1;
    Q.y = 1;
    P.x = X + Y;
    P.y = 1;
    P.x = P.x + P.y;
    Ligne L;
    L.A = P;
    L.B = Q;
    return(L.A)
}

