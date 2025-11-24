<?php

namespace MauticPlugin\EmailPluginBundle\EventListener;

use Mautic\EmailBundle\Event\EmailSendEvent;
use Mautic\EmailBundle\EmailEvents;
use Mautic\CoreBundle\Model\AuditLogModel;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Contracts\HttpClient\HttpClientInterface;


class EmailSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private AuditLogModel $auditLogModel,
        private HttpClientInterface $client
    ) {
    }

    public static function getSubscribedEvents(): array
    {
        return [
            EmailEvents::EMAIL_ON_SEND    => ['onEmailSend', -99999],
        ];
    }

    public function onEmailSend(EmailSendEvent $event): void
    {
        $payload = [
            'lead' => (array) $event->getLead(),
            'content' => $event->getContent(true),
            'subject' => $event->getSubject(),
            'source' => $event->getSource(),
        ];

        # Fill SS trigger url here
        $url = '';
        $this->client->request('POST', $url, [
            'json' => $payload,
        ]);
        $log = [
            'bundle'    => 'asset',
            'object'    => 'asset',
            'objectId'  => 1,
            'action'    => 'external',
            'details'   => $payload,
            'ipAddress' => '',
        ];
        $this->auditLogModel->writeToLog($log);
    }
}
