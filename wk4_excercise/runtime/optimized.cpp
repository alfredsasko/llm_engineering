#include <iostream>
#include <iomanip>
#include <chrono>
#include <omp.h>

double calculate(long long iterations, int param1, int param2) {
    const double p1 = static_cast<double>(param1);
    const double p2 = static_cast<double>(param2);
    const double p1_squared = p1 * p1;
    const double p2_squared = p2 * p2;
    const double term_numerator = -2.0 * p2;
    
    double sum = 0.0;
    
    #pragma omp parallel for reduction(+:sum)
    for (long long i = 1; i <= iterations; ++i) {
        double i_d = static_cast<double>(i);
        sum += term_numerator / (i_d * i_d * p1_squared - p2_squared);
    }
    
    return 1.0 + sum;
}

int main() {
    std::ios_base::sync_with_stdio(false);
    std::cin.tie(NULL);

    const long long iterations = 100000000;
    const int param1 = 4;
    const int param2 = 1;
    
    const auto start_time = std::chrono::high_resolution_clock::now();
    
    const double result = calculate(iterations, param1, param2) * 4.0;
    
    const auto end_time = std::chrono::high_resolution_clock::now();
    
    const std::chrono::duration<double> elapsed_time = end_time - start_time;
    
    std::cout << std::fixed;
    std::cout << "Result: " << std::setprecision(12) << result << '\n';
    std::cout << "Execution Time: " << std::setprecision(6) << elapsed_time.count() << " seconds" << '\n';
    
    return 0;
}