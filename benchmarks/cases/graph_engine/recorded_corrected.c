#include <stdio.h>
#include <string.h>

#define LIMIT 32
#define INF 4000000000000000LL

static long long graph[LIMIT][LIMIT];
static int vertices;

static void reset_graph(int size)
{
    int i;
    int j;
    vertices = size;
    for (i = 0; i < vertices; ++i) {
        for (j = 0; j < vertices; ++j) {
            graph[i][j] = i == j ? 0 : INF;
        }
    }
}

static void add_edge(int from, int to, int weight)
{
    if (from >= 0 && from < vertices && to >= 0 && to < vertices) {
        if (graph[from][to] < 0 || weight < graph[from][to]) {
            graph[from][to] = weight;
        }
    }
}

static int closest_unvisited(const long long distance[], const int used[])
{
    long long best = INF;
    int chosen = -1;
    int i;
    for (i = 0; i < vertices; ++i) {
        if (!used[i] && distance[i] < best) {
            best = distance[i];
            chosen = i;
        }
    }
    return chosen;
}

static void shortest_paths(int source, long long distance[])
{
    int used[LIMIT] = {0};
    int i;
    int step;
    for (i = 0; i < vertices; ++i) {
        distance[i] = INF;
    }
    distance[source] = 0;
    for (step = 0; step < vertices; ++step) {
        int node = closest_unvisited(distance, used);
        int next;
        if (node < 0) {
            break;
        }
        used[node] = 1;
        for (next = 0; next < vertices; ++next) {
            if (graph[node][next] < INF) {
                long long candidate = distance[node] + graph[node][next];
                if (candidate < distance[next]) {
                    distance[next] = candidate;
                }
            }
        }
    }
}

static int minimum_hops(int source, int target)
{
    int queue[LIMIT];
    int hops[LIMIT];
    int head = 0;
    int tail = 0;
    int i;
    for (i = 0; i < vertices; ++i) {
        hops[i] = -1;
    }
    hops[source] = 0;
    queue[tail++] = source;
    while (head < tail) {
        int node = queue[head++];
        int next;
        for (next = 0; next < vertices; ++next) {
            if (graph[node][next] >= 0 && graph[node][next] < INF && hops[next] < 0) {
                hops[next] = hops[node] + 1;
                queue[tail++] = next;
            }
        }
    }
    return hops[target];
}

static void print_distance(long long distance)
{
    if (distance == INF) {
        printf("INF");
    } else {
        printf("%lld", distance);
    }
}

static void print_all(int source)
{
    long long distance[LIMIT];
    int i;
    shortest_paths(source, distance);
    for (i = 0; i < vertices; ++i) {
        if (i != 0) {
            putchar(' ');
        }
        if (distance[i] == INF) {
            printf("INF");
        } else {
            printf("%lld", distance[i]);
        }
    }
    putchar('\n');
}

static int reachable_count(int source)
{
    long long distance[LIMIT];
    int result = 0;
    int i;
    shortest_paths(source, distance);
    for (i = 0; i < vertices; ++i) {
        if (distance[i] != INF) {
            ++result;
        }
    }
    return result;
}

static void print_round_sum(int source)
{
    long long distance[LIMIT];
    long long total = 0;
    int i;
    shortest_paths(source, distance);
    for (i = 0; i < vertices; ++i) {
        if (distance[i] == INF) {
            puts("INF");
            return;
        }
        total += distance[i];
    }
    printf("%lld\n", total);
}

static void process_command(void)
{
    char command[16];
    int source;
    int target;
    int weight;
    long long distance[LIMIT];
    scanf("%15s", command);
    if (strcmp(command, "EDGE") == 0) {
        scanf("%d%d%d", &source, &target, &weight);
        add_edge(source, target, weight);
        puts("OK");
    } else if (strcmp(command, "DIST") == 0) {
        scanf("%d%d", &source, &target);
        shortest_paths(source, distance);
        print_distance(distance[target]);
        putchar('\n');
    } else if (strcmp(command, "ALL") == 0) {
        scanf("%d", &source);
        print_all(source);
    } else if (strcmp(command, "BFS") == 0) {
        scanf("%d%d", &source, &target);
        printf("%d\n", minimum_hops(source, target));
    } else if (strcmp(command, "REACH") == 0) {
        scanf("%d", &source);
        printf("%d\n", reachable_count(source));
    } else if (strcmp(command, "ROUND") == 0) {
        scanf("%d", &source);
        print_round_sum(source);
    } else if (strcmp(command, "RESET") == 0) {
        reset_graph(vertices);
        puts("OK");
    }
}

int main(void)
{
    int edges;
    int commands;
    int size;
    int i;
    if (scanf("%d%d%d", &size, &edges, &commands) != 3) {
        return 0;
    }
    reset_graph(size);
    for (i = 0; i < edges; ++i) {
        int from;
        int to;
        int weight;
        scanf("%d%d%d", &from, &to, &weight);
        add_edge(from, to, weight);
    }
    for (i = 0; i < commands; ++i) {
        process_command();
    }
    return 0;
}
