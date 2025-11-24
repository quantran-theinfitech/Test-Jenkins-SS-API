FROM rabbitmq:3-management

# Download and install the delayed message exchange plugin
RUN apt-get update && apt-get install -y wget && \
    cd /opt/rabbitmq/plugins && \
    wget https://github.com/rabbitmq/rabbitmq-delayed-message-exchange/releases/download/v3.13.0/rabbitmq_delayed_message_exchange-3.13.0.ez && \
    rabbitmq-plugins enable rabbitmq_delayed_message_exchange && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
