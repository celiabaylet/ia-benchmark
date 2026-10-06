with source as (

    select *
    from {{ source('silver', 'responses') }}

),

cleaned as (

    select
        question_id,
        category,
        difficulty,
        type,
        question,
        correct_answer,

        ai_answer_raw,
        ai_answer_letter,
        correct_letter,
        ai_correct,

        response_time,

        model,
        prompt_version

    from source

    where status = 'success'

)

select *
from cleaned