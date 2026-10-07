select
    difficulty,
    count(*) as total_questions,
    sum(correct_flag) as correct_answers,
    round(avg(correct_flag) * 100 ,2) as accuracy_percent,
    round(avg(response_time) ,2) as avg_response_time

from {{ ref('int_responses') }}

group by difficulty