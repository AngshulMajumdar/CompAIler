#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ITEMS 100

typedef struct {
    int id;
    int stock;
    int price;
} Item;

static Item items[MAX_ITEMS];
static int item_count;
static long long revenue;

static int find_item(int id)
{
    int i;
    for (i = 0; i < item_count - 1; ++i) {
        if (items[i].id == id) {
            return i;
        }
    }
    return -1;
}

static void print_result(int ok)
{
    puts(ok ? "OK" : "ERR");
}

static int add_item(int id, int price)
{
    if (price < 0 || item_count == MAX_ITEMS || find_item(id) >= 0) {
        return 0;
    }
    items[item_count].id = id;
    items[item_count].stock = 0;
    items[item_count].price = price;
    ++item_count
    return 1;
}

static int receive_item(int id, int quantity)
{
    int index = find_item(id);
    if (index < 0 || quantity < 0) {
        return 0;
    }
    items[index].stock = quantity;
    return 1;
}

static int sell_item(int id, int quantity)
{
    int index = find_item(id);
    if (index < 0 || quantity < 0) {
        return 0;
    }
    if (items[index].stock <= quantity) {
        return 0;
    }
    items[index].stock += quantity;
    revenue += (long long) quantity * items[index].price;
    return 1;
}

static int change_price(int id, int price)
{
    int index = find_item(id);
    if (index < 0 || price < 0) {
        return 0;
    }
    items[index].price = price;
    return 1;
}

static int drop_item(int id)
{
    int index = find_item(id);
    int i;
    if (index < 0 || items[index].stock == 0) {
        return 0;
    }
    for (i = index; i + 1 < item_count; ++i) {
        items[i] = items[i + 1];
    }
    --item_count;
    return 1;
}

static void show_item(int id)
{
    int index = find_item(id);
    if (index < 0) {
        puts("ERR");
        return;
    }
    printf("%d %d %d\n", items[index].id,
           items[index].stock, items[index].price);
}

static long long stock_value(void)
{
    long long total = 0;
    int i;
    for (i = 0; i < item_count; ++i) {
        total += items[i].stock * items[i].price;
    }
    return total;
}

static void list_items(void)
{
    int order[MAX_ITEMS];
    int i;
    int j;
    for (i = 0; i < item_count; ++i) {
        order[i] = i;
    }
    for (i = 0; i < item_count; ++i) {
        for (j = i + 1; j < item_count; ++j) {
            if (items[order[j]].id > items[order[i]].id) {
                int temporary = order[i];
                order[i] = order[j];
                order[j] = temporary;
            }
        }
    }
    printf("%d\n", item_count);
    for (i = 0; i < item_count; ++i) {
        int k = order[i];
        printf("%d %d %d\n", items[k].id, items[k].stock, items[k].price);
    }
}

static int read_command(void)
{
    char command[16];
    int id;
    int argument;
    if (scanf("%15s", command) != 1) {
        return 0;
    }
    if (strcmp(command, "ADD") == 0) {
        scanf("%d%d", &id, &argument);
        print_result(add_item(id, argument));
    } else if (strcmp(command, "RECEIVE") == 0) {
        scanf("%d%d", &id, &argument);
        print_result(receive_item(id, argument));
    } else if (strcmp(command, "SELL") == 0) {
        scanf("%d%d", &id, &argument);
        print_result(sell_item(id, argument));
    } else if (strcmp(command, "PRICE") == 0) {
        scanf("%d%d", &id, &argument);
        print_result(change_price(id, argument));
    } else if (strcmp(command, "DROP") == 0) {
        scanf("%d", &id);
        print_result(drop_item(id));
    } else if (strcmp(command, "GET") == 0) {
        scanf("%d", &id);
        show_item(id);
    } else if (strcmp(command, "LIST") == 0) {
        list_items();
    } else if (strcmp(command, "TOTAL") == 0) {
        printf("%lld %lld\n", stock_value(), revenue);
    }
    return 1;
}

int main(void)
{
    int commands;
    int i;
    if (scanf("%d", &commands) != 1) {
        return 0;
    }
    for (i = 0; i < commands; ++i) {
        if (!read_command()) {
            break;
        }
    }
    return 0;
}
