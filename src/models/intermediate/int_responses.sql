select
    question_id,
    category,
    difficulty,
    type,
    model,
    prompt_version,
    ai_correct,
    response_time,

    case
        when ai_correct = true then 1
        else 0
    end as correct_flag

from {{ ref('stg_responses') }}