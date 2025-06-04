double main(double X, double Y) {
    int Z = 1;
    while(X) {
        X = X - Z;
        Y = Y + 0.1;
    };
    printf(Y);
    return(Y);
}