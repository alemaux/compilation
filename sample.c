double main(double X, double Y) {
    double Z = 1.2;
    while(X) {
        X = X - 0.1;
        Y = Y + 0.1;
    };
    printf(Y);
    return(Y);
}