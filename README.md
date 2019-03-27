# tap-linkedin

Simple singer-tap

To use add a config.json
```
{
  "access_token": "token"
  "start_date": "2019-01-01",
  "end_date": "2019-01-01",
  "account_id": "account_id",
  "timeGranularity": "DAILY"
}
```

`tap-linkedin -c config.json --catalog catalog.json`

## Docker

Map volume to run docker

`docker run -v /path/to/tap/:opt/app/ tap-linkedin`