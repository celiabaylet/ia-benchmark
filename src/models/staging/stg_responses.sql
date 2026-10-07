with responses as (

    select *
    from {{ source('silver', 'responses') }}

),

questions as (

    select *
    from {{ source('silver', 'questions') }}

)

select
    r.question_id,

    q.category,
    q.difficulty,
    q.type,
    q.question,
    q.correct_answer,

    r.ai_answer_raw,
    r.ai_answer_letter,
    r.correct_letter,
    r.ai_correct,
    r.response_time,
    r.model,
    r.prompt_version,
    r.status

from responses r

left join questions q
    on r.question_id = q.question_id

where r.status = 'success'