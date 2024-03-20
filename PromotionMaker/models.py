from django.db import models


# Create your models here.
class Chat(models.Model):
    chat_id = models.IntegerField(default=0, verbose_name="Ідентифікатор чату")
    title = models.CharField(max_length=300,verbose_name="Назва")
    class Meta:
        verbose_name = "чат"
        verbose_name_plural = "чати"

    def __str__(self):
        return self.title

    def get_posts(self):
        return self.post_set.all()
class Post(models.Model):
    title = models.CharField(max_length=600, verbose_name="Текст повідомлення")
    chat_id = models.ForeignKey(Chat, on_delete=models.CASCADE,verbose_name="Чат")
    description = models.TextField(verbose_name="Опис")
    class Meta:
        verbose_name = "пост"
        verbose_name_plural = "пости"

    def __str__(self):
        return self.title

    def get_buttons(self):
        return self.button_set.all()


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
