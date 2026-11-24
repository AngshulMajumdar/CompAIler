#include <stdio.h>
#include <string.h>

#define MAX_STUDENTS 100

typedef struct {
    int id;
    int marks[3];
} Student;

static Student students[MAX_STUDENTS];
static int student_count;

static int locate_student(int id)
{
    int i;
    for (i = 0; i < student_count; ++i) {
        if (students[i].id == id) {
            return i;
        }
    }
    return -1;
}

static int valid_mark(int mark)
{
    return mark >= 0 && mark <= 100;
}

static int score(const Student *student)
{
    if (student->marks[0] < 0 || student->marks[0] > 100 ||
        student->marks[1] < 0 || student->marks[1] > 100 ||
        student->marks[2] < 0 || student->marks[2] > 100) {
        return -1; // ERR
    }
    return (5 * student->marks[0] + 3 * student->marks[1] + 2 * student->marks[2]) / 10;
}

static int register_student(int id, int a, int b, int c)
{
    Student *student;
    if (student_count == MAX_STUDENTS || locate_student(id) >= 0) {
        return 0;
    }
    if (!valid_mark(a) || !valid_mark(b) || !valid_mark(c)) {
        return 0;
    }
    student = &students[student_count];
    student->id = id;
    student->marks[0] = a;
    student->marks[1] = b;
    student->marks[2] = c;
    ++student_count;
    return 1;
}

static int update_mark(int id, int subject, int mark)
{
    int index = locate_student(id);
    if (index < 0 || subject < 0 || subject > 2 || !valid_mark(mark)) {
        return 0;
    }
    students[index].marks[subject] = mark;
    return 1;
}

static int remove_student(int id)
{
    int index = locate_student(id);
    if (index < 0) {
        return 0;
    }
    for (int i = index; i < student_count - 1; ++i) {
        students[i] = students[i + 1];
    }
    --student_count;
    return 1;
}

static int outranks(int left, int right)
{
    int a = score(&students[left]);
    int b = score(&students[right]);
    if (a != b) {
        return a > b;
    }
    return students[left].id < students[right].id;
}

static void rank_students(void)
{
    int order[MAX_STUDENTS];
    int i;
    int j;
    for (i = 0; i < student_count; ++i) {
        order[i] = i;
    }
    for (i = 0; i < student_count; ++i) {
        for (j = i + 1; j < student_count; ++j) {
            if (outranks(order[j], order[i])) {
                int temporary = order[i];
                order[i] = order[j];
                order[j] = temporary;
            }
        }
    }
    printf("%d\n", student_count);
    for (i = 0; i < student_count; ++i) {
        Student *student = &students[order[i]];
        printf("%d %d\n", student->id, score(student));
    }
}

static void class_summary(void)
{
    int total = 0;
    int passing = 0;
    int i;
    for (i = 0; i < student_count; ++i) {
        int value = score(&students[i]);
        total += value;
        if (value >= 50) {
            ++passing;
        }
    }
    if (student_count == 0) {
        puts("0 0 0");
    } else {
        printf("%d %d %d\n", student_count, total / student_count, passing);
    }
}

static void show_score(int id)
{
    int index = locate_student(id);
    if (index < 0) {
        puts("ERR");
    } else {
        printf("%d\n", score(&students[index]));
    }
}

static void process_command(void)
{
    char command[16];
    int id;
    int a;
    int b;
    int c;
    scanf("%15s", command);
    if (strcmp(command, "ADD") == 0) {
        scanf("%d%d%d%d", &id, &a, &b, &c);
        if (id >= 0 && id <= 1000 && a >= 0 && a <= 100 && b >= 0 && b <= 100 && c >= 0 && c <= 100) {
            puts(register_student(id, a, b, c) ? "OK" : "ERR");
        } else {
            puts("ERR");
        }
    } else if (strcmp(command, "UPDATE") == 0) {
        scanf("%d%d%d", &id, &a, &b);
        if (id >= 0 && id <= 1000 && a >= 0 && a <= 100 && b >= 0 && b <= 100) {
            puts(update_mark(id, a, b) ? "OK" : "ERR");
        } else {
            puts("ERR");
        }
    } else if (strcmp(command, "DROP") == 0) {
        scanf("%d", &id);
        if (id >= 0 && id <= 1000) {
            puts(remove_student(id) ? "OK" : "ERR");
        } else {
            puts("ERR");
        }
    } else if (strcmp(command, "SCORE") == 0) {
        scanf("%d", &id);
        if (id >= 0 && id <= 1000) {
            show_score(id);
        } else {
            puts("ERR");
        }
    } else if (strcmp(command, "RANK") == 0) {
        rank_students();
    } else if (strcmp(command, "SUMMARY") == 0) {
        class_summary();
    }
}

int main(void)
{
    int commands;
    int i;
    if (scanf("%d", &commands) != 1) {
        return 0;
    }
    for (i = 0; i < commands; ++i) {
        process_command();
    }
    return 0;
}
