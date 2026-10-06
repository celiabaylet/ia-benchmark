select
    model,
    category,
    count(*) as total_questions,
    sum(correct_flag) as correct_answers,
    avg(correct_flag) * 100 as accuracy

from {{ ref('int_responses') }}

group by
    model,
    category