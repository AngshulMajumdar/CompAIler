#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ENTRIES 2048

typedef struct {
    int row;
    int column;
    long long value;
} Entry;

typedef struct {
    int rows;
    int columns;
    int count;
    Entry entries[MAX_ENTRIES];
} Matrix;

static void initialize_matrix(Matrix *matrix, int rows, int columns)
{
    matrix->rows = rows;
    matrix->columns = columns;
    matrix->count = 0;
    memset(matrix->entries, 0, sizeof(matrix->entries));
}

static int find_entry(const Matrix *matrix, int row, int column)
{
    int i;
    for (i = 0; i < matrix->count; ++i) {
        if (matrix->entries[i].row == row && matrix->entries[i].column == column) {
            return i;
        }
    }
    return -1;
}

static void add_entry(Matrix *matrix, int row, int column, long long value)
{
    int index = find_entry(matrix, row, column);
    if (index >= 0) {
        matrix->entries[index].value += value;
        if (matrix->entries[index].value == 0) {
            for (int i = index; i < matrix->count - 1; i++) {
                matrix->entries[i] = matrix->entries[i + 1];
            }
            matrix->count--;
        }
    } else {
        if (matrix->count < MAX_ENTRIES) {
            Entry *entry = &matrix->entries[matrix->count++];
            entry->row = row;
            entry->column = column;
            entry->value = value;
        }
    }
}

static int compare_entries(const void *left, const void *right)
{
    const Entry *a = (const Entry *) left;
    const Entry *b = (const Entry *) right;
    if (a->row != b->row) {
        return a->row - b->row;
    }
    return a->column - b->column;
}

static void remove_zeros(Matrix *matrix)
{
    int read;
    int write = 0;
    for (read = 0; read < matrix->count; ++read) {
        if (matrix->entries[read].value != 0) {
            matrix->entries[write++] = matrix->entries[read];
        }
    }
    matrix->count = write;
}

static void normalize(Matrix *matrix)
{
    remove_zeros(matrix);
    qsort(matrix->entries, matrix->count, sizeof(Entry), compare_entries);
}

static void read_entries(Matrix *matrix, int number)
{
    int i;
    for (i = 0; i < number; ++i) {
        int row;
        int column;
        long long value;
        scanf("%d%d%lld", &row, &column, &value);
        if (row >= 0 && row < matrix->rows && column >= 0 && column < matrix->columns) {
            add_entry(matrix, row, column, value);
        }
    }
}

static void transpose_matrix(const Matrix *input, Matrix *output)
{
    int i;
    initialize_matrix(output, input->columns, input->rows);
    for (i = 0; i < input->count; ++i) {
        Entry entry = input->entries[i];
        add_entry(output, entry.column, entry.row, entry.value);
    }
}

static void add_matrices(const Matrix *a, const Matrix *b, Matrix *output)
{
    int i;
    initialize_matrix(output, a->rows, a->columns);
    for (i = 0; i < a->count; ++i) {
        Entry entry = a->entries[i];
        add_entry(output, entry.row, entry.column, entry.value);
    }
    for (i = 0; i < b->count; ++i) {
        Entry entry = b->entries[i];
        add_entry(output, entry.row, entry.column, entry.value);
    }
}

static void multiply_matrices(const Matrix *a, const Matrix *b, Matrix *output)
{
    int i;
    int j;
    initialize_matrix(output, a->rows, b->columns);
    for (i = 0; i < a->count; ++i) {
        for (j = 0; j < b->count; ++j) {
            if (a->entries[i].column == b->entries[j].column) {
                long long product = a->entries[i].value * b->entries[j].value;
                add_entry(output, a->entries[i].row, b->entries[j].column, product);
            }
        }
    }
}

static void print_matrix(Matrix *matrix)
{
    int i;
    normalize(matrix);
    printf("%d %d %d\n", matrix->rows, matrix->columns, matrix->count);
    for (i = 0; i < matrix->count; ++i) {
        Entry entry = matrix->entries[i];
        printf("%d %d %lld\n", entry.row, entry.column, entry.value);
    }
}

static void process_transpose(void)
{
    int rows;
    int columns;
    int count;
    Matrix input;
    Matrix result;
    scanf("%d%d%d", &rows, &columns, &count);
    initialize_matrix(&input, rows, columns);
    read_entries(&input, count);
    transpose_matrix(&input, &result);
    print_matrix(&result);
}

static void process_binary(const char *operation)
{
    int rows;
    int inner;
    int columns;
    int first;
    int second;
    Matrix a;
    Matrix b;
    Matrix result;
    if (strcmp(operation, "ADD") == 0) {
        scanf("%d%d%d%d", &rows, &columns, &first, &second);
        inner = columns;
        initialize_matrix(&b, rows, columns);
    } else {
        scanf("%d%d%d%d%d", &rows, &inner, &columns, &first, &second);
        initialize_matrix(&b, inner, columns);
    }
    initialize_matrix(&a, rows, inner);
    read_entries(&a, first);
    read_entries(&b, second);
    if (strcmp(operation, "ADD") == 0) {
        add_matrices(&a, &b, &result);
    } else {
        multiply_matrices(&a, &b, &result);
    }
    print_matrix(&result);
}

int main(void)
{
    int operations;
    int i;
    if (scanf("%d", &operations) != 1) {
        return 0;
    }
    for (i = 0; i < operations; ++i) {
        char operation[16];
        scanf("%15s", operation);
        if (strcmp(operation, "TRANS") == 0) {
            process_transpose();
        } else {
            process_binary(operation);
        }
    }
    return 0;
}
