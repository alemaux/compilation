double main(double X, double Y) {
    double Z = 0.1;
    while(X) {
        X = X - Z;
        Y = Y + 0.1;
        Z = 1 + 2;
    };
    printf(Y);
    return(Y);
}