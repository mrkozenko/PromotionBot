from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from PromotionMaker.models import Chat, InviteToChatModel


# Create your views here.
def index(request):
    if request.method == 'POST':
        # Отримання даних з POST запиту
        chat_id = request.POST.get('chat_select')
        users_list = request.POST.get('users')
        print(f"{chat_id} - chat found")
        db_chat = None
        # Перевірка, чи chat_id валідний
        try:
            db_chat = Chat.objects.filter(chat_id=int(chat_id)).first()
        except Chat.DoesNotExist:
            # Обробка ситуації, коли чат не знайдено
            return HttpResponse('Чат не знайдено.', status=400)
        for user in users_list.split('\n'):
            print(db_chat)
            InviteToChatModel(chat_id=db_chat,username=user).save()
        # Збереження даних у базу даних
        print("db saved")
        return HttpResponse("All good")

    else:
        all_chats = Chat.objects.all()
        if len(all_chats) > 0:
            context = {"chats":all_chats}
            template = loader.get_template('index.html')
            return HttpResponse(template.render(context, request))
        else:
            return HttpResponse("Чати відсутні в базі")
