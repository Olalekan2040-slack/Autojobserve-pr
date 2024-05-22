from autojobserve.models import AllJobs

# def job_exists(db, url):
#          return db.query(AllJobs).filter(AllJobs.job_permalink == url).first() is not None

def save_Glassdoor_jobs(db, company_name,job_title, job_salary,is_easy_apply, location, job_description, url):
    #if not  job_exists(db, url):
        new_job = AllJobs(
            job_title=job_title,
            auto_apply= is_easy_apply,
            job_location =location,
            job_description=job_description,
            job_salary = job_salary,
            company_name = company_name,
            job_permalink = url
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        print(new_job)


