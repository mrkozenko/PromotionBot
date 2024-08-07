from django.db import models


# Create your models here.
class Chat(models.Model):
    chat_id = models.IntegerField(default=0, verbose_name="Ідентифікатор чату")
    title = models.CharField(max_length=300, verbose_name="Назва")

    class Meta:
        verbose_name = "чат"
        verbose_name_plural = "чати"

    def __str__(self):
        return self.title

    def get_posts(self):
        return self.post_set.all()

    def get_community_for_subscribe(self):
        return self.subscribe_links.first()


class Post(models.Model):
    title = models.CharField(max_length=600, verbose_name="Текст повідомлення")
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE, verbose_name="Чат")
    description = models.TextField(verbose_name="Опис")

    class Meta:
        verbose_name = "пост"
        verbose_name_plural = "пости"

    def __str__(self):
        return self.title

    def get_buttons(self):
        return self.button_set.all().order_by('priority')


class Button(models.Model):
    priority = models.IntegerField(verbose_name="Порядок відображення")
    title = models.CharField(max_length=200, verbose_name="Текст відображення кнопки")
    url = models.CharField(max_length=600, verbose_name="Посилання в кнопці")
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "кнопка"
        verbose_name_plural = "кнопки"

    def __str__(self):
        return self.title


# модель для підписки в потрібних чатах на вказані чати
class SubscribeLink(models.Model):
    # чат де будуть просити підписку
    chat_id = models.ForeignKey(Chat, on_delete=models.DO_NOTHING, verbose_name="Базовий чат",
                                related_name="subscribe_links")
    # чат куди потрібно підписатись
    subscribe_chat = models.ForeignKey(Chat, on_delete=models.DO_NOTHING, verbose_name="Спільнота для підписки",
                                       related_name="subscribed_links")
    subscribe_link = models.CharField(max_length=200, verbose_name="Посилання для підписки", default=" ")

    class Meta:
        verbose_name = "Підписку"
        verbose_name_plural = "Підписки"

    def __str__(self):
        return self.subscribe_link


class PromotionPost(models.Model):
    # автоматизація публікації оголошень
    class Meta:
        verbose_name = "Рекламний пост"
        verbose_name_plural = "Рекламні пости"

    # чат де будуть просити підписку
    # додає користувач
    chat_id = models.ForeignKey(Chat, on_delete=models.DO_NOTHING, verbose_name="Чат для реклами", null=True,
                                blank=True,
                                related_name="promotion_posts")
    end_date_promotion = models.DateField(verbose_name="Дата завершення постингу", null=True)
    # додає алгоритм
    message_id = models.IntegerField(verbose_name="ID повідомлення поста реклами")
    chat_message_id = models.IntegerField(verbose_name="ID чату реклами")


class SpamFilterModel(models.Model):
    # автоматизація видалення заборонених слів
    class Meta:
        verbose_name = "Спам-фільтр"
        verbose_name_plural = "Спам-фільтри"

    black_words = models.CharField(max_length=1000, verbose_name="Заборонені слова")
    except_ids = models.CharField(max_length=1000, verbose_name="ID рекламодавців виключень")


class InviteToChatModel(models.Model):
    class Meta:
        verbose_name = "Інвайт в чат"
        verbose_name_plural = "Інвайти в чат"

    chat_id = models.ForeignKey(Chat, on_delete=models.DO_NOTHING, verbose_name="Чат інвайту", null=True,
                                blank=True,
                                related_name="invite_to_chat")
    username = models.CharField(max_length=500,verbose_name="Нікнейм юзера")

    is_invited = models.BooleanField( null=True,
                                blank=True,default=False)