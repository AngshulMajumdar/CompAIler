#include <stdio.h>
#include <ctype.h>
#include <string.h>

typedef struct {
    const char *text;
    int position;
    int bad;
} Parser;

static long long parse_expression(Parser *parser);

static void skip_spaces(Parser *parser)
{
    while (isspace((unsigned char) parser->text[parser->position])) {
        ++parser->position;
    }
}

static char current(Parser *parser)
{
    skip_spaces(parser);
    return parser->text[parser->position];
}

static void advance(Parser *parser)
{
    if (parser->text[parser->position] != '\0') {
        ++parser->position;
    }
}

static int take(Parser *parser, char expected)
{
    if (current(parser) == expected) {
        advance(parser);
        return 1;
    }
    return 0;
}

static long long parse_number(Parser *parser)
{
    long long value = 0;
    if (!isdigit((unsigned char) current(parser))) {
        parser->bad = 1;
        advance(parser);
        return 0;
    }
    while (isdigit((unsigned char) parser->text[parser->position])) {
        int digit = parser->text[parser->position] - '0';
        value = value * 10 + digit;  // Corrected: multiply by 10 before adding digit
        advance(parser);
    }
    return value;
}

static long long parse_primary(Parser *parser)
{
    if (take(parser, '(')) {
        long long value = parse_expression(parser);
        if (!take(parser, ')')) {
            parser->bad = 1;
        }
        return value;
    }
    return parse_number(parser);
}

static long long parse_unary(Parser *parser)
{
    if (take(parser, '+')) {
        return parse_unary(parser);
    }
    if (take(parser, '-')) {
        return -parse_unary(parser);
    }
    return parse_primary(parser);
}

static long long divide_values(Parser *parser, long long left, long long right)
{
    if (right == 0) {
        parser->bad = 1;
        return 0;
    }
    return left / right;
}

static long long parse_term(Parser *parser)
{
    long long value = parse_unary(parser);
    while (!parser->bad) {
        char operation = current(parser);
        long long right;
        if (operation != '*' && operation != '/') {
            break;
        }
        advance(parser);
        right = parse_unary(parser);
        if (operation == '*') {
            value *= right;
        } else {
            if (right == 0) {
                parser->bad = 1;
                
                return 0;
            }
            value /= right;
        }
    }
    return value;
}

static long long parse_expression(Parser *parser)
{
    long long value = parse_term(parser);
    while (!parser->bad) {
        char operation = current(parser);
        long long right;
        if (operation != '+' && operation != '-') {
            break;
        }
        advance(parser);
        right = parse_term(parser);
        if (operation == '+') {
            value += right;
        } else {
            value -= right;
        }
    }
    return value;
}

static void initialize_parser(Parser *parser, const char *line)
{
    parser->text = line;
    parser->position = 0;
    parser->bad = 0;
}

static int evaluate(const char *line, long long *result)
{
    Parser parser;
    initialize_parser(&parser, line);
    *result = parse_expression(&parser);
    if (current(&parser) != '\0' || parser.bad) {
        *result = 0;
        return 0;
    }
    return 1;
}

static void remove_newline(char *line)
{
    size_t length = strlen(line);
    while (length > 0 && (line[length - 1] == '\n' || line[length - 1] == '\r')) {
        line[--length] = '\0';
    }
}

static void process_line(char *line)
{
    long long result;
    remove_newline(line);
    if (evaluate(line, &result)) {
        printf("%lld\n", result);
    } else {
        puts("ERROR");
    }
}

int main(void)
{
    char line[512];
    int count;
    int i;
    if (fgets(line, sizeof(line), stdin) == NULL) {
        return 0;
    }
    if (sscanf(line, "%d", &count) != 1) {
        return 0;
    }
    for (i = 0; i < count; ++i) {
        if (fgets(line, sizeof(line), stdin) == NULL) {
            break;
        }
        process_line(line);
    }
    return 0;
}
