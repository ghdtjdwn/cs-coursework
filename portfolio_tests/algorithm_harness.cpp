#include "hw1_myheader.h"

#include <array>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

using Sort = std::function<void(iterator, iterator)>;

bool run_case(const std::string &name, const Sort &sort) {
    std::vector<MyInteger> values;
    for (int value : std::array<int, 8>{5, -1, 5, 2, 0, 9, -7, 3}) {
        values.emplace_back(value);
    }

    default_logger.ClearCounts();
    sort(values.begin(), values.end());

    const std::array<int, 8> expected{-7, -1, 0, 2, 3, 5, 5, 9};
    for (std::size_t index = 0; index < expected.size(); ++index) {
        if (static_cast<int>(values[index]) != expected[index]) {
            std::cerr << name << ": wrong order at index " << index << '\n';
            return false;
        }
    }
    if (default_logger.count_copy_constructor_called != 0 ||
        default_logger.count_copy_assignment_called != 0) {
        std::cerr << name << ": copied MyInteger values during sort\n";
        return false;
    }
    return true;
}

int main() {
    default_logger.SetLogFunctions(false, false, false);
    const std::array<std::pair<std::string, Sort>, 4> cases{{
        {"insertion_sort", [](iterator begin, iterator end) { insertion_sort(begin, end); }},
        {"selection_sort", [](iterator begin, iterator end) { selection_sort(begin, end); }},
        {"merge_sort", [](iterator begin, iterator end) { merge_sort(begin, end); }},
        {"quicksort", [](iterator begin, iterator end) { quicksort(begin, end); }},
    }};

    for (const auto &[name, sort] : cases) {
        if (!run_case(name, sort)) {
            return 1;
        }
    }
    std::cout << "4 sorting algorithms passed with zero copies\n";
    return 0;
}
