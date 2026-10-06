select
    model,
    difficulty,
    count(*) as total_questions,
    sum(correct_flag) as correct_answers,
    avg(correct_flag) * 100 as accuracy,
    avg(response_time) as avg_response_time

from {{ ref('int_responses') }}

group by
    model,
    difficulty