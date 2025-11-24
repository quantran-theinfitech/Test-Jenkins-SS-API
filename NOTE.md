# ALEMBIC
**Step 1: Cập nhật phiên bản alembic mới nhất**
`git pull`

**Step 2: Kiểm tra các head của alembic**
`alembic heads`
>Example result:
>879b73418b51 (head)
>e8abcb42971a (head)

**Step 3: Tạo file migration mới**
`alembic revision --autogenerate --head {id} -m "message"`
(Nếu có 2 head, chọn 1 trong 2 head, thường là head mới hơn (trong ví dụ là e8abcb42971a))

**Step 4: Modify the file with your migration**
Chỉnh sửa lại file được tạo từ bước 3
Xóa tất cả những thay đổi không chủ đích cập nhật được tạo ra từ --autogenerate

**Step 5: Upgrade your db with new version**
`alembic upgrade heads`
(PHẢI kiểm tra kỹ lại file ở bước 4 (giá trị down_revision, các trường mới, các hàm upgrade, downgrade, v.v.) trước khi chạy bước này)

# GIT (LƯU Ý có 2 nhánh đặc biệt quan trọng là dev_v2 và stg_v2)
**RULE 1: KHÔNG DÙNG SQUASH COMMIT KHI TẠO PR VÀO stg_v2 (production)**

**RULE 2: KHÔNG ĐƯỢC PUSH FORCE VÀO stg_v2**
Không được sử dụng `push --force` vào stg_v2
Không được push trực tiếp stg_v2 (tương tự với dev_v2)

**RULE 3: KHÔNG ĐƯỢC PUSH FORCE VÀO dev_v2**
Không được sử dụng `push --force` vào dev_v2
Luôn tạo Pull Request trước khi merge vào dev_v2




# HOW TO RUN THIS APP
**Step 1: Create .env**
Tạo file .env
Copy nội dung từ env.example sang file .env

**Step 2: Chạy Docker Compose**
`docker compose up -d --build`

Ứng dụng sẽ chạy ở port có giá trị {APP_PORT} được khai báo trong file ".env". Kiểm tra trong docker-compose:
"${APP_PORT:-8000}:8000", nếu APP_PORT không tồn tại trong ".env" thì APP_PORT = 8000.
Sử dụng Postman (hoặc công cụ khác) để test các route API.



# CELERY
Chạy worker:
`celery -A celery_worker worker --loglevel=info`
Chạy lịch định kỳ (beat schedule):
`celery -A celery_worker beat --loglevel=info`
Gọi task thủ công:
`celery -A celery_worker call {tên task}`

# REDIS
Chạy local:
Sửa lại bỏ ssl với kết nối redis (deps.py, celery init nếu chạy cả celery )
