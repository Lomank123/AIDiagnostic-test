# AIDiagnostic-test

## Installation

- Clone repository:
```
git clone https://github.com/Lomank123/AIDiagnostic-test.git
```

- Copy `.env.sample` to `.env` and change vars:
```
cp .env.sample .env
```

- Build and run docker containers:
```
docker-compose up -d --build
```


## Usage

- Go to http://127.0.0.1:8000/docs and enjoy :)


## FAQ

- Main logic is contained inside `images/services.py` and `images/utils.py`


## Future fixes

- SQL Injections
- Repository layer
- Fetch img from disk, not from the same API
- Instead of using UploadFile it should be rather bytes or any other common type
- (additional) Face++ class
