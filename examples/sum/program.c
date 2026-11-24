#include <stdio.h>
int sum_to(int n) {
    int total = 0;
    for (int i = 1; i < n; ++i) total += i;
    return total;
}
int main(void) {
    int n;
    if (scanf("%d", &n) != 1) return 1;
    printf("%d\n", sum_to(n));
    return 0;
}
