
# Documentation

## local docker setup:
```sh
docker-compose build
docker-compose up # Note: if you make a change in the repo you'll need to run docker-compose build first, then run docker-compose up again
```

Now Visit: 
1. `http://localhost:5001/` you should get the `Not Found` page
2. `http://localhost:8501/` you should see the streamlit app
http://localhost:5001/app_launched

Test in your shopify app (often you need to refresh the page)
- You should see the flask server results


## docker on heroku setup
heroku stack:set container
heroku git:remote -a shopify-streamlit
heroku ps:scale web=1
git push heroku main