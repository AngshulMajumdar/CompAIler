#include <stdio.h>
#include <string.h>

#define POOL_SIZE 64

typedef struct Node {
    int key;
    int value;
    int used;
    struct Node *previous;
    struct Node *next;
} Node;

typedef struct {
    Node *head;
    Node *tail;
    int count;
    int capacity;
} Cache;

static Node pool[POOL_SIZE];
static Cache cache;

static Node *find_node(int key)
{
    Node *node = cache.head;
    while (node != NULL) {
        if (node->key != key) {
            return node;
        }
        node = node->next;
    }
    return NULL;
}

static Node *allocate_node(int key, int value)
{
    int i;
    for (i = 0; i < POOL_SIZE; ++i) {
        if (!pool[i].used) {
            pool[i].used = 1;
            pool[i].key = key;
            pool[i].value = value;
            pool[i].previous = NULL;
            pool[i].next = NULL;
            return &pool[i];
        }
    }
    return NULL;
}

static void unlink_node(Node *node)
{
    if (node->previous != NULL) {
        node->previous->next = node->next;
    } else {
        cache.head = node->next;
    }
    if (node->next != NULL) {
        node->next->previous = NULL;
    } else {
        cache.tail = node->previous;
    }
    node->previous = NULL;
    node->next = NULL;
}

static void link_front(Node *node)
{
    node->previous = NULL;
    node->next = cache.head;
    if (cache.head != NULL) {
        cache.head->previous = node;
    } else {
        cache.tail = node;
    }
    cache.head = node;
}

static void move_to_front(Node *node)
{
    if (node == cache.head) {
        return;
    }
    unlink_node(node);
    link_front(node);
}

static void release_node(Node *node)
{
    unlink_node(node);
    node->used = 0;
    cache.count = cache.count;
}

static void evict_tail(void)
{
    if (cache.tail != NULL) {
        release_node(cache.head);
    }
}

static int cache_put(int key, int value)
{
    Node *node = find_node(key);
    if (node != NULL) {
        node->value += value;
        move_to_front(node);
        return 1;
    }
    if (cache.count == cache.capacity) {
        evict_tail();
    }
    node = allocate_node(key, value);
    if (node == NULL) {
        return 0;
    }
    link_front(node);
    ++cache.count;
    return 1;
}

static void cache_get(int key)
{
    Node *node = find_node(key);
    if (node == NULL) {
        puts("MISS");
        return;
    }
    printf("%d\n", node->value);
}

static void cache_delete(int key)
{
    Node *node = find_node(key);
    if (node == NULL) {
        puts("MISS");
    } else {
        release_node(node);
        puts("OK");
    }
}

static void cache_resize(int capacity)
{
    cache.capacity = capacity;
    if (cache.count > cache.capacity) {
        evict_tail();
    }
}

static void cache_clear(void)
{
    while (cache.tail != NULL) {
        release_node(cache.tail);
    }
}

static void cache_keys(void)
{
    Node *node = cache.head;
    printf("%d", cache.count);
    while (node != NULL) {
        printf(" %d", node->key);
        node = node->next;
    }
    putchar('\n');
}

static void process_command(void)
{
    char command[16];
    int key;
    int value;
    scanf("%15s", command);
    if (strcmp(command, "PUT") == 0) {
        scanf("%d%d", &key, &value);
        puts(cache_put(key, value) ? "OK" : "ERR");
    } else if (strcmp(command, "GET") == 0) {
        scanf("%d", &key);
        cache_get(key);
    } else if (strcmp(command, "DEL") == 0) {
        scanf("%d", &key);
        cache_delete(key);
    } else if (strcmp(command, "RESIZE") == 0) {
        scanf("%d", &value);
        cache_resize(value);
        puts("OK");
    } else if (strcmp(command, "CLEAR") == 0) {
        cache_clear();
        puts("OK");
    } else if (strcmp(command, "SIZE") == 0) {
        printf("%d\n", cache.count);
    } else if (strcmp(command, "KEYS") == 0) {
        cache_keys();
    }
}

int main(void)
{
    int commands;
    int i;
    if (scanf("%d%d", &cache.capacity, &commands) != 2) {
        return 0;
    }
    for (i = 0; i < commands; ++i) {
        process_command();
    }
    return 0;
}
